package main

import "testing"

func TestSeedQuestionsNotEmpty(t *testing.T) {
	if len(questions) == 0 {
		t.Fatal("expected seed questions")
	}
}
