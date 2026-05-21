import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: Number(__ENV.K6_VUS || 50),
  duration: __ENV.K6_DURATION || "5m",
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<800"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://traefik";
const SUBJECTS = ["history", "physics", "math", "geography"];

export default function () {
  const subject = SUBJECTS[Math.floor(Math.random() * SUBJECTS.length)];

  const ready = http.get(`${BASE_URL}/api/${subject}/readyz`, {
    tags: { endpoint: "readyz", subject },
  });
  check(ready, { "readyz is 200": (r) => r.status === 200 });

  const list = http.get(`${BASE_URL}/api/${subject}/v1/questions?limit=5`, {
    tags: { endpoint: "questions", subject },
  });
  check(list, { "list is 200": (r) => r.status === 200 });

  sleep(1);
}
