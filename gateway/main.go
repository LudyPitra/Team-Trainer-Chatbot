package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/google/uuid"
)

type ChatRequest struct {
	Message string `json:"message"`
}

type PythonRequest struct {
	SessionID uuid.UUID `json:"session_id"`
	Message   string    `json:"message"`
}

type PythonResponse struct {
	Reply string `json:"reply"`
}

// Handler da Rota de Chat
func handleChat(w http.ResponseWriter, r *http.Request) {
	// 1. Apenas requisições POST
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 2. Decodificação do JSON do Front-end
	var chatReq ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&chatReq); err != nil {
		http.Error(w, "Error to read JSON", http.StatusBadRequest)
		return
	}

	// 3. Gerenciamento de Sessão Seguro (Cookies HTTP-Only)
	cookieName := "novamente_session"
	var sessionID uuid.UUID

	cookie, err := r.Cookie(cookieName)
	if err != nil {
		fmt.Println("New session detected. Genereting ID...")
		sessionID = uuid.New()

		http.SetCookie(w, &http.Cookie{
			Name:     cookieName,
			Value:    sessionID.String(),
			Path:     "/",
			HttpOnly: true, // Protection against XSS
			MaxAge:   3600, // Expire in 1 hour
		})
	} else {
		parsedID, parseErr := uuid.Parse(cookie.Value)
		if parseErr != nil {
			http.Error(w, "Invalid Session", http.StatusUnauthorized)
			return
		}
		sessionID = parsedID
		fmt.Printf("Existing session recognized: %s\n", sessionID)
	}

	// 4. Preparando a mensagem para o Motor de IA
	pythonReq := PythonRequest{
		SessionID: sessionID,
		Message:   chatReq.Message,
	}
	jsonData, _ := json.Marshal(pythonReq)

	// 5. Cliente HTTP com Timeout (Proteção contra travamento do Event Loop)
	client := &http.Client{
		Timeout: 0,
	}

	reqToPython, err := http.NewRequest(http.MethodPost, "http://localhost:8000/api/chat", bytes.NewBuffer(jsonData))
	if err != nil {
		http.Error(w, "Internal error while assembling the request.", http.StatusInternalServerError)
		return
	}
	reqToPython.Header.Set("Content-Type", "application/json")

	// 6. Fazendo a chamada ao Python
	resp, err := client.Do(reqToPython)
	if err != nil {
		fmt.Printf("Error in the python AI engine: %v\n", err)
		http.Error(w, "Error to connect to AI engine", http.StatusInternalServerError)
		return
	}
	defer func() {
		_ = resp.Body.Close()
	}()

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	buf := make([]byte, 1024)

	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			_, writeErr := w.Write(buf[:n])
			if writeErr != nil {
				fmt.Printf("Error writing to client: %v\n", writeErr)
				break
			}
			flusher.Flush()
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			fmt.Printf("Error reading stream: %v\n", err)
			break
		}
	}
}

// Inicialização do Servidor Maestro
func main() {
	fmt.Println("🐹 Maestro starting at gate 8080...")

	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		_, _ = fmt.Fprintf(w, "The Maestro is alive and listening to requests!")
		fmt.Printf("I received a visit on route %s\n", r.URL.Path)
	})

	http.HandleFunc("/api/chat", handleChat)

	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Fatal Error in the Server:", err)
	}
}
