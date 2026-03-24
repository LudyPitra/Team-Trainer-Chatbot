package main

import (
	"fmt"
	"net/http"
)

func main() {
	fmt.Println("🐹 Maestro starting at gate 8080...")

	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		_, _ = fmt.Fprintf(w, "The Maestro is alive and listening to requests!")
		fmt.Printf("I received a visit on route %s\n", r.URL.Path)
	})

	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Fatal Error in the Server:", err)
	}
}
