import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 50,
  duration: "5m",
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<800"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://traefik";

export default function () {
  const res = http.get(`${BASE_URL}/api/physics/health/ready`);
  check(res, {
    "status is 200": (r) => r.status === 200,
  });
  sleep(1);
}
