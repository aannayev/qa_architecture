package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"slices"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

type question struct {
	ID           string   `json:"id"`
	ExternalID   string   `json:"external_id"`
	Topic        string   `json:"topic"`
	Difficulty   string   `json:"difficulty"`
	Prompt       string   `json:"prompt"`
	Options      []string `json:"options"`
	CorrectIndex int      `json:"-"`
	Explanation  string   `json:"-"`
}

type topicInfo struct {
	Topic         string `json:"topic"`
	QuestionCount int    `json:"question_count"`
}

type submitRequest struct {
	SelectedIndex int `json:"selected_index"`
}

type submitResult struct {
	QuestionID   string `json:"question_id"`
	Correct      bool   `json:"correct"`
	CorrectIndex int    `json:"correct_index"`
	Explanation  string `json:"explanation"`
}

var questions = []question{
	{
		ID:           uuid.MustParse("11111111-1111-1111-1111-111111111111").String(),
		ExternalID:   "math-algebra-001",
		Topic:        "algebra",
		Difficulty:   "easy",
		Prompt:       "What is x if 2x + 6 = 14?",
		Options:      []string{"2", "3", "4", "5"},
		CorrectIndex: 2,
		Explanation:  "2x = 8, so x = 4.",
	},
	{
		ID:           uuid.MustParse("22222222-2222-2222-2222-222222222222").String(),
		ExternalID:   "math-geometry-001",
		Topic:        "geometry",
		Difficulty:   "medium",
		Prompt:       "How many degrees are in a triangle?",
		Options:      []string{"90", "180", "270", "360"},
		CorrectIndex: 1,
		Explanation:  "The sum of interior angles in a triangle is 180 degrees.",
	},
	{
		ID:           uuid.MustParse("33333333-3333-3333-3333-333333333333").String(),
		ExternalID:   "math-calculus-001",
		Topic:        "calculus",
		Difficulty:   "hard",
		Prompt:       "What is the derivative of x^2?",
		Options:      []string{"x", "2x", "x^2", "2"},
		CorrectIndex: 1,
		Explanation:  "d/dx(x^2) = 2x.",
	},
}

func main() {
	router := chi.NewRouter()
	router.Get("/healthz", liveness)
	router.Get("/readyz", readiness)
	router.Get("/v1/topics", listTopics)
	router.Get("/v1/questions", listQuestions)
	router.Get("/v1/questions/{questionID}", getQuestion)
	router.Post("/v1/questions/{questionID}/submit", submitAnswer)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	log.Printf("math service started on :%s", port)
	if err := http.ListenAndServe(":"+port, router); err != nil {
		log.Fatal(err)
	}
}

func liveness(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func readiness(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ready"})
}

func listTopics(w http.ResponseWriter, _ *http.Request) {
	counter := map[string]int{}
	for _, q := range questions {
		counter[q.Topic]++
	}

	resp := make([]topicInfo, 0, len(counter))
	for topic, count := range counter {
		resp = append(resp, topicInfo{Topic: topic, QuestionCount: count})
	}
	writeJSON(w, http.StatusOK, resp)
}

func listQuestions(w http.ResponseWriter, r *http.Request) {
	topic := r.URL.Query().Get("topic")
	difficulty := r.URL.Query().Get("difficulty")
	limit := 20

	if raw := r.URL.Query().Get("limit"); raw != "" {
		if parsed, err := strconv.Atoi(raw); err == nil && parsed > 0 && parsed <= 100 {
			limit = parsed
		}
	}

	filtered := make([]question, 0, len(questions))
	for _, q := range questions {
		if topic != "" && q.Topic != topic {
			continue
		}
		if difficulty != "" && q.Difficulty != difficulty {
			continue
		}
		filtered = append(filtered, publicQuestion(q))
	}

	if len(filtered) > limit {
		filtered = filtered[:limit]
	}
	writeJSON(w, http.StatusOK, filtered)
}

func getQuestion(w http.ResponseWriter, r *http.Request) {
	questionID := chi.URLParam(r, "questionID")
	for _, q := range questions {
		if q.ID == questionID {
			writeJSON(w, http.StatusOK, publicQuestion(q))
			return
		}
	}
	writeJSON(w, http.StatusNotFound, map[string]string{"detail": "question not found"})
}

func submitAnswer(w http.ResponseWriter, r *http.Request) {
	questionID := chi.URLParam(r, "questionID")
	var body submitRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"detail": "invalid request body"})
		return
	}

	for _, q := range questions {
		if q.ID != questionID {
			continue
		}
		if body.SelectedIndex < 0 || body.SelectedIndex >= len(q.Options) {
			writeJSON(w, http.StatusUnprocessableEntity, map[string]string{"detail": "selected_index out of range"})
			return
		}
		result := submitResult{
			QuestionID:   q.ID,
			Correct:      body.SelectedIndex == q.CorrectIndex,
			CorrectIndex: q.CorrectIndex,
			Explanation:  q.Explanation,
		}
		writeJSON(w, http.StatusOK, result)
		return
	}

	writeJSON(w, http.StatusNotFound, map[string]string{"detail": "question not found"})
}

func publicQuestion(q question) question {
	q.CorrectIndex = 0
	q.Explanation = ""
	return q
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func init() {
	for _, q := range questions {
		if len(q.Options) == 0 || !slices.Contains([]string{"easy", "medium", "hard"}, q.Difficulty) {
			log.Fatalf("invalid seed question: %s", q.ExternalID)
		}
	}
}
