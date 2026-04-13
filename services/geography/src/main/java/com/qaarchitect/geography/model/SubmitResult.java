package com.qaarchitect.geography.model;

import java.util.UUID;

public record SubmitResult(
        UUID question_id,
        boolean correct,
        int correct_index,
        String explanation
) {
}
