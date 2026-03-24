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

func handleChat(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var chatReq ChatRequest
	err := json.NewDecoder(r.Body).Decode(&chatReq)
	if err != nil {
		http.Error(w, "Error reading JSON", http.StatusBadRequest)
		return
	}

	sessionID := uuid.New()

	pythonReq := PythonRequest{
		SessionID: sessionID,
		Message:   chatReq.Message,
	}

	jsonData, _ := json.Marshal(pythonReq)

	resp, err := http.Post("http://localhost:8000/api/chat", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		http.Error(w, "Error to conect with AI brain", http.StatusInternalServerError)
		return
	}

	defer func() {
		_ = resp.Body.Close()
	}()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Failed to send response to client: %v\n", err)
	}
	w.Header().Set("Content-Type", "application/json")
	_, err = w.Write(body)
	if err != nil {
		fmt.Printf("Failed to send response to client: %v\n", err)
	}
}

func main() {
	http.HandleFunc("/chat", handleChat)

	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Fatal Error in the Server:", err)
	}
}
