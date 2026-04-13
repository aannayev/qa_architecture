package com.qaarchitect.geography.service;

import com.qaarchitect.geography.model.Question;
import com.qaarchitect.geography.model.TopicInfo;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class QuestionService {
    private final List<Question> questions = List.of(
            new Question(
                    UUID.fromString("44444444-4444-4444-4444-444444444444"),
                    "geo-capital-001",
                    "capitals",
                    "easy",
                    "What is the capital of France?",
                    List.of("Paris", "Madrid", "Rome", "Berlin"),
                    0,
                    "Paris is the capital and largest city of France."
            ),
            new Question(
                    UUID.fromString("55555555-5555-5555-5555-555555555555"),
                    "geo-physical-001",
                    "physical-geography",
                    "medium",
                    "Which is the longest river in the world?",
                    List.of("Amazon", "Nile", "Yangtze", "Mississippi"),
                    1,
                    "The Nile is traditionally considered the longest river."
            ),
            new Question(
                    UUID.fromString("66666666-6666-6666-6666-666666666666"),
                    "geo-climate-001",
                    "climate",
                    "hard",
                    "What does Köppen Cfb climate generally indicate?",
                    List.of("Polar tundra", "Humid subtropical", "Oceanic temperate", "Hot desert"),
                    2,
                    "Cfb in Köppen classification corresponds to temperate oceanic climate."
            )
    );

    public List<TopicInfo> topics() {
        Map<String, Long> grouped = questions.stream()
                .collect(Collectors.groupingBy(Question::topic, Collectors.counting()));
        return grouped.entrySet().stream()
                .map(e -> new TopicInfo(e.getKey(), e.getValue().intValue()))
                .toList();
    }

    public List<Question> listQuestions(String topic, String difficulty, int limit) {
        return questions.stream()
                .filter(q -> topic == null || topic.isBlank() || q.topic().equals(topic))
                .filter(q -> difficulty == null || difficulty.isBlank() || q.difficulty().equals(difficulty))
                .limit(limit)
                .map(this::publicView)
                .toList();
    }

    public Optional<Question> getQuestion(UUID id) {
        return questions.stream().filter(q -> q.id().equals(id)).findFirst().map(this::publicView);
    }

    public Optional<Question> findOriginal(UUID id) {
        return questions.stream().filter(q -> q.id().equals(id)).findFirst();
    }

    private Question publicView(Question q) {
        return new Question(q.id(), q.external_id(), q.topic(), q.difficulty(), q.prompt(), q.options(), -1, "");
    }
}
