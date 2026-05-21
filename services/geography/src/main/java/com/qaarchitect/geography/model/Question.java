package com.qaarchitect.geography.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record Question(
        UUID id,
        @JsonProperty("external_id") String external_id,
        String topic,
        String difficulty,
        String prompt,
        List<String> options,
        @JsonProperty("correct_index") Integer correctIndex,
        String explanation
) {
}
