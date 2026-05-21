package com.qaarchitect.geography.service;

import com.qaarchitect.geography.model.Question;
import com.qaarchitect.geography.model.QuestionPublic;
import com.qaarchitect.geography.model.TopicInfo;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class QuestionServiceTests {

    private final QuestionService service = new QuestionService();

    @Test
    void topicsContainExpectedSubjects() {
        List<TopicInfo> topics = service.topics();
        assertFalse(topics.isEmpty(), "topics should not be empty");
        assertTrue(
                topics.stream().anyMatch(t -> t.topic().equals("capitals")),
                "expected 'capitals' topic"
        );
    }

    @Test
    void listQuestionsReturnsPublicViewWithoutAnswerFields() {
        List<QuestionPublic> qs = service.listQuestions(null, null, 10);
        assertFalse(qs.isEmpty());
        for (QuestionPublic q : qs) {
            assertNotNull(q.id());
            assertFalse(q.options().isEmpty());
        }
    }

    @Test
    void listQuestionsFilterByTopic() {
        List<QuestionPublic> qs = service.listQuestions("capitals", null, 10);
        assertFalse(qs.isEmpty());
        for (QuestionPublic q : qs) {
            assertEquals("capitals", q.topic());
        }
    }

    @Test
    void listQuestionsFilterByDifficulty() {
        List<QuestionPublic> hard = service.listQuestions(null, "hard", 10);
        for (QuestionPublic q : hard) {
            assertEquals("hard", q.difficulty());
        }
    }

    @Test
    void listQuestionsRespectsLimit() {
        List<QuestionPublic> qs = service.listQuestions(null, null, 1);
        assertEquals(1, qs.size());
    }

    @Test
    void getQuestionReturnsPublicView() {
        UUID capitalId = UUID.fromString("44444444-4444-4444-4444-444444444444");
        Optional<QuestionPublic> q = service.getQuestion(capitalId);
        assertTrue(q.isPresent());
        assertEquals("What is the capital of France?", q.get().prompt());
    }

    @Test
    void findOriginalReturnsCorrectAnswer() {
        UUID capitalId = UUID.fromString("44444444-4444-4444-4444-444444444444");
        Optional<Question> q = service.findOriginal(capitalId);
        assertTrue(q.isPresent());
        assertEquals(0, q.get().correctIndex(), "Paris is the first option");
        assertNotNull(q.get().explanation());
    }

    @Test
    void unknownIdReturnsEmpty() {
        UUID missing = UUID.fromString("00000000-0000-0000-0000-000000000000");
        assertTrue(service.getQuestion(missing).isEmpty());
        assertTrue(service.findOriginal(missing).isEmpty());
    }
}
