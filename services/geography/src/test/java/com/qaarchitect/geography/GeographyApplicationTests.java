package com.qaarchitect.geography;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class GeographyApplicationTests {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void contextLoads() {
    }

    @Test
    void listQuestionsDoesNotExposeCorrectIndex() throws Exception {
        String body = mockMvc.perform(get("/v1/questions?limit=1"))
                .andExpect(status().isOk())
                .andReturn()
                .getResponse()
                .getContentAsString();

        JsonNode payload = objectMapper.readTree(body);
        assertThat(payload.isArray()).isTrue();
        assertThat(payload).isNotEmpty();
        assertThat(payload.get(0).has("correctIndex")).isFalse();
        assertThat(payload.get(0).has("correct_index")).isFalse();
        assertThat(payload.get(0).has("explanation")).isFalse();
    }

    @Test
    void submitCorrectAnswer() throws Exception {
        String listBody = mockMvc.perform(get("/v1/questions?topic=capitals&limit=1"))
                .andExpect(status().isOk())
                .andReturn()
                .getResponse()
                .getContentAsString();

        JsonNode question = objectMapper.readTree(listBody).get(0);
        String questionId = question.get("id").asText();

        mockMvc.perform(post("/v1/questions/" + questionId + "/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"selected_index\":0}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.correct").value(true))
                .andExpect(jsonPath("$.correct_index").value(0));
    }

    @Test
    void submitOutOfRangeReturns422() throws Exception {
        String listBody = mockMvc.perform(get("/v1/questions?limit=1"))
                .andExpect(status().isOk())
                .andReturn()
                .getResponse()
                .getContentAsString();

        String questionId = objectMapper.readTree(listBody).get(0).get("id").asText();

        mockMvc.perform(post("/v1/questions/" + questionId + "/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"selected_index\":99}"))
                .andExpect(status().isUnprocessableEntity());
    }
}
