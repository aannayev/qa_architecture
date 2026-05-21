package com.qaarchitect.geography.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class QuestionControllerTests {

    @Autowired
    private MockMvc mockMvc;

    private MockMvc mvc() {
        return mockMvc;
    }

    @BeforeEach
    void setUp() {
        // Spring Boot wires QuestionService automatically via @Service.
    }

    @Test
    void healthzReturns200() throws Exception {
        mvc().perform(get("/healthz"))
                .andExpect(status().isOk());
    }

    @Test
    void readyzReturns200() throws Exception {
        mvc().perform(get("/readyz"))
                .andExpect(status().isOk());
    }

    @Test
    void topicsEndpointReturnsList() throws Exception {
        mvc().perform(get("/v1/topics"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    void questionsListUsesSnakeCaseAndHidesAnswer() throws Exception {
        mvc().perform(get("/v1/questions?limit=5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$[0].external_id").exists())
                .andExpect(jsonPath("$[0].correct_index").doesNotExist())
                .andExpect(jsonPath("$[0].explanation").doesNotExist())
                .andExpect(jsonPath("$[0].correctIndex").doesNotExist());
    }

    @Test
    void getQuestionByIdHidesAnswer() throws Exception {
        mvc().perform(get("/v1/questions/44444444-4444-4444-4444-444444444444"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("44444444-4444-4444-4444-444444444444"))
                .andExpect(jsonPath("$.correct_index").doesNotExist())
                .andExpect(jsonPath("$.correctIndex").doesNotExist());
    }

    @Test
    void getUnknownQuestionReturns404() throws Exception {
        mvc().perform(get("/v1/questions/00000000-0000-0000-0000-000000000000"))
                .andExpect(status().isNotFound());
    }

    @Test
    void submitCorrectAnswerReturnsTrue() throws Exception {
        // Paris is at index 0 for the capitals question.
        mvc().perform(post("/v1/questions/44444444-4444-4444-4444-444444444444/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"selected_index\":0}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.correct").value(true))
                .andExpect(jsonPath("$.correct_index").value(0));
    }

    @Test
    void submitWrongAnswerReturnsFalse() throws Exception {
        mvc().perform(post("/v1/questions/44444444-4444-4444-4444-444444444444/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"selected_index\":1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.correct").value(false))
                .andExpect(jsonPath("$.correct_index").value(0));
    }

    @Test
    void submitOutOfRangeReturns422() throws Exception {
        mvc().perform(post("/v1/questions/44444444-4444-4444-4444-444444444444/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"selected_index\":99}"))
                .andExpect(status().isUnprocessableEntity());
    }

    @Test
    void submitNegativeIndexReturns422() throws Exception {
        mvc().perform(post("/v1/questions/44444444-4444-4444-4444-444444444444/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"selected_index\":-1}"))
                .andExpect(status().isUnprocessableEntity());
    }
}
