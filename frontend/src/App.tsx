import { useEffect, useMemo, useRef, useState } from "react";
import { fetchQuestions, submitAnswer } from "./api";
import type { QuestionPublic, Subject } from "./types";

const SUBJECTS: Subject[] = ["history", "physics", "math", "geography"];

type QuizState = "pick" | "loading" | "answering" | "result";

export function App() {
  const [state, setState] = useState<QuizState>("pick");
  const [subject, setSubject] = useState<Subject | null>(null);
  const [questions, setQuestions] = useState<QuestionPublic[]>([]);
  const [index, setIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [assistantInput, setAssistantInput] = useState("");
  const [assistantMessages, setAssistantMessages] = useState<string[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const wsUrl = (import.meta.env.VITE_AI_WS_URL as string | undefined) ?? "ws://localhost/ai/v1/assist";

  const current = useMemo(() => questions[index], [questions, index]);

  async function startExam(nextSubject: Subject) {
    setError(null);
    setState("loading");
    setSubject(nextSubject);
    try {
      const loaded = await fetchQuestions(nextSubject);
      setQuestions(loaded);
      setIndex(0);
      setScore(0);
      setState("answering");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setState("pick");
    }
  }

  async function answer(optionIndex: number) {
    if (!current || !subject) {
      return;
    }
    try {
      const result = await submitAnswer(subject, current.id, optionIndex);
      if (result.correct) {
        setScore((s) => s + 1);
      }

      if (index + 1 < questions.length) {
        setIndex((i) => i + 1);
      } else {
        setState("result");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }

  function reset() {
    setState("pick");
    setSubject(null);
    setQuestions([]);
    setIndex(0);
    setScore(0);
    setError(null);
    setAssistantMessages([]);
  }

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  function ensureSocket() {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      return socketRef.current;
    }

    const sessionId = `${subject ?? "exam"}-${Date.now()}`;
    const connector = wsUrl.includes("?") ? "&" : "?";
    const socket = new WebSocket(`${wsUrl}${connector}session_id=${encodeURIComponent(sessionId)}`);
    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as { content?: string };
        if (parsed.content) {
          setAssistantMessages((prev) => [...prev, `assistant: ${parsed.content}`]);
        }
      } catch {
        setAssistantMessages((prev) => [...prev, `assistant: ${event.data}`]);
      }
    };
    socketRef.current = socket;
    return socket;
  }

  function askAssistant() {
    const message = assistantInput.trim();
    if (!message) {
      return;
    }
    const socket = ensureSocket();
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(message);
    } else {
      socket.addEventListener(
        "open",
        () => {
          socket.send(message);
        },
        { once: true },
      );
    }
    setAssistantMessages((prev) => [...prev, `you: ${message}`]);
    setAssistantInput("");
  }

  return (
    <main className="container">
      <h1>AI Quality Architect Exam Platform</h1>
      {error ? <div className="error">{error}</div> : null}

      {state === "pick" ? (
        <section className="card">
          <h2>Select exam subject</h2>
          <div className="grid">
            {SUBJECTS.map((item) => (
              <button key={item} onClick={() => startExam(item)} className="button">
                {item}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {state === "loading" ? (
        <section className="card">
          <h2>Loading questions...</h2>
        </section>
      ) : null}

      {state === "answering" && current ? (
        <section className="card">
          <h2>
            Subject: <span className="accent">{subject}</span>
          </h2>
          <p className="muted">
            Question {index + 1} / {questions.length}
          </p>
          <p className="question">{current.prompt}</p>
          <div className="grid">
            {current.options.map((option, optionIndex) => (
              <button key={option} onClick={() => answer(optionIndex)} className="button">
                {option}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {state === "result" ? (
        <section className="card">
          <h2>Exam completed</h2>
          <p>
            Subject: <span className="accent">{subject}</span>
          </p>
          <p>
            Score: <strong>{score}</strong> / {questions.length}
          </p>
          <button className="button" onClick={reset}>
            Start new exam
          </button>
        </section>
      ) : null}

      <section className="card">
        <h2>AI Assistant</h2>
        <p className="muted">Ask for hints and explanations (without direct answers).</p>
        <div className="assistant-log">
          {assistantMessages.length === 0 ? <p className="muted">No messages yet.</p> : null}
          {assistantMessages.map((msg, idx) => (
            <p key={`${msg}-${idx}`}>{msg}</p>
          ))}
        </div>
        <div className="assistant-input">
          <input
            value={assistantInput}
            onChange={(event) => setAssistantInput(event.target.value)}
            placeholder="Ask for a hint..."
          />
          <button className="button" onClick={askAssistant}>
            Send
          </button>
        </div>
      </section>
    </main>
  );
}
