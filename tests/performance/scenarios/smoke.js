import http from "k6/http";
import { check, group } from "k6";

export const options = {
  vus: 1,
  iterations: 10,
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<500"],
    "checks{kind:readyz}": ["rate>0.95"],
    "checks{kind:questions}": ["rate>0.95"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://traefik";
const SUBJECTS = ["history", "physics", "math", "geography"];

export default function () {
  for (const subject of SUBJECTS) {
    group(`readyz/${subject}`, () => {
      const r = http.get(`${BASE_URL}/api/${subject}/readyz`);
      check(
        r,
        { [`${subject} readyz is 200`]: (res) => res.status === 200 },
        { kind: "readyz", subject },
      );
    });

    group(`questions/${subject}`, () => {
      const r = http.get(`${BASE_URL}/api/${subject}/v1/questions?limit=1`);
      check(
        r,
        {
          [`${subject} questions is 200`]: (res) => res.status === 200,
          [`${subject} questions is JSON array`]: (res) => {
            try {
              return Array.isArray(res.json());
            } catch (_e) {
              return false;
            }
          },
        },
        { kind: "questions", subject },
      );
    });
  }
}
