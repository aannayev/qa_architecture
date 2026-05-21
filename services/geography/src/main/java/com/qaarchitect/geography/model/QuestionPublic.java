package com.qaarchitect.geography.model;

import java.util.List;
import java.util.UUID;

public record QuestionPublic(
        UUID id,
        String external_id,
        String topic,
        String difficulty,
        String prompt,
        List<String> options
) {
}
