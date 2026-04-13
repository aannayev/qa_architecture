import http from "k6/http";
import { check } from "k6";

export const options = {
  vus: 1,
  iterations: 10,
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<500"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://traefik";

export default function () {
  const res = http.get(`${BASE_URL}/api/history/health/ready`);
  check(res, {
    "status is 200": (r) => r.status === 200,
  });
}
