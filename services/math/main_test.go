package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/go-chi/chi/v5"
)

func testRouter() http.Handler {
	router := chi.NewRouter()
	router.Get("/v1/questions", listQuestions)
	router.Get("/v1/questions/{questionID}", getQuestion)
	router.Post("/v1/questions/{questionID}/submit", submitAnswer)
	return router
}

func TestSeedQuestionsNotEmpty(t *testing.T) {
	if len(questions) == 0 {
		t.Fatal("expected seed questions")
	}
}

func TestListQuestionsDoesNotExposeCorrectIndex(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/v1/questions?limit=1", nil)
	rec := httptest.NewRecorder()
	testRouter().ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	var payload []question
	if err := json.NewDecoder(rec.Body).Decode(&payload); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if len(payload) == 0 {
		t.Fatal("expected at least one question")
	}

	body := rec.Body.String()
	if bytes.Contains([]byte(body), []byte(`"correct_index"`)) {
		t.Fatalf("correct_index must not appear in list response: %s", body)
	}
}

func TestSubmitCorrectAnswer(t *testing.T) {
	q := questions[0]
	body, _ := json.Marshal(submitRequest{SelectedIndex: q.CorrectIndex})
	req := httptest.NewRequest(http.MethodPost, "/v1/questions/"+q.ID+"/submit", bytes.NewReader(body))
	rec := httptest.NewRecorder()
	testRouter().ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d body=%s", rec.Code, rec.Body.String())
	}

	var result submitResult
	if err := json.NewDecoder(rec.Body).Decode(&result); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if !result.Correct {
		t.Fatalf("expected correct answer, got %+v", result)
	}
	if result.CorrectIndex != q.CorrectIndex {
		t.Fatalf("expected correct_index=%d, got %d", q.CorrectIndex, result.CorrectIndex)
	}
}

func TestSubmitOutOfRangeReturns422(t *testing.T) {
	q := questions[0]
	body, _ := json.Marshal(submitRequest{SelectedIndex: len(q.Options) + 10})
	req := httptest.NewRequest(http.MethodPost, "/v1/questions/"+q.ID+"/submit", bytes.NewReader(body))
	rec := httptest.NewRecorder()
	testRouter().ServeHTTP(rec, req)

	if rec.Code != http.StatusUnprocessableEntity {
		t.Fatalf("expected 422, got %d body=%s", rec.Code, rec.Body.String())
	}
}

func TestGetQuestionNotFound(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/v1/questions/00000000-0000-0000-0000-000000000000", nil)
	rec := httptest.NewRecorder()
	testRouter().ServeHTTP(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", rec.Code)
	}
}
