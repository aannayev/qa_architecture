package com.qaarchitect.geography.controller;

import com.qaarchitect.geography.model.Question;
import com.qaarchitect.geography.model.SubmitRequest;
import com.qaarchitect.geography.model.SubmitResult;
import com.qaarchitect.geography.model.TopicInfo;
import com.qaarchitect.geography.service.QuestionService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/v1")
@CrossOrigin(origins = "*")
public class QuestionController {
    private final QuestionService questionService;

    public QuestionController(QuestionService questionService) {
        this.questionService = questionService;
    }

    @GetMapping("/topics")
    public List<TopicInfo> topics() {
        return questionService.topics();
    }

    @GetMapping("/questions")
    public List<Question> listQuestions(
            @RequestParam(required = false) String topic,
            @RequestParam(required = false) String difficulty,
            @RequestParam(defaultValue = "20") int limit
    ) {
        int normalizedLimit = Math.max(1, Math.min(limit, 100));
        return questionService.listQuestions(topic, difficulty, normalizedLimit);
    }

    @GetMapping("/questions/{questionId}")
    public Question getQuestion(@PathVariable UUID questionId) {
        return questionService.getQuestion(questionId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "question not found"));
    }

    @PostMapping("/questions/{questionId}/submit")
    public SubmitResult submit(
            @PathVariable UUID questionId,
            @RequestBody SubmitRequest request
    ) {
        Question original = questionService.findOriginal(questionId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "question not found"));
        if (request.selected_index() < 0 || request.selected_index() >= original.options().size()) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY, "selected_index out of range");
        }
        return new SubmitResult(
                original.id(),
                request.selected_index() == original.correctIndex(),
                original.correctIndex(),
                original.explanation()
        );
    }
}
