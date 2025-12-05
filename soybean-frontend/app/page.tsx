"use client";

import React, { useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

type User = {
  id: number;
  name: string;
  email: string;
};

type Prediction = {
  id: number;
  image_url: string;
  predicted_label: string;
  confidence: number | null;
  model_version: string;
  created_at: string;
};

type Feedback = {
  id: number;
  user_id: number;
  prediction_id: number;
  rating: number | null;
  is_correct: boolean | null;
  comment: string | null;
  created_at: string;
};

export default function HomePage() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [tab, setTab] = useState<"auth" | "predict" | "history">("auth");
  const [message, setMessage] = useState<string | null>(null);

  // ---------- SIGNUP STATE ----------
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");

  // ---------- LOGIN STATE ----------
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // ---------- PREDICT STATE ----------
  const [file, setFile] = useState<File | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [predictMsg, setPredictMsg] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // ---------- FEEDBACK STATE ----------
  const [fbCorrect, setFbCorrect] = useState<"yes" | "no">("yes");
  const [fbRating, setFbRating] = useState(5);
  const [fbComment, setFbComment] = useState("");
  const [fbMsg, setFbMsg] = useState<string | null>(null);

  // ---------- HISTORY STATE ----------
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // ========== SIMPLE API HELPERS ==========

  async function apiGet(path: string, token?: string) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    return res;
  }

  async function apiPost(
    path: string,
    body?: any,
    token?: string,
    isFormData: boolean = false
  ) {
    const headers: Record<string, string> = token
      ? { Authorization: `Bearer ${token}` }
      : {};

    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: isFormData
        ? headers
        : {
            "Content-Type": "application/json",
            ...headers,
          },
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    });
    return res;
  }

  // ========== AUTH HANDLERS ==========

  async function handleSignup() {
    setMessage(null);
    const res = await apiPost("/users/", {
      name: signupName,
      email: signupEmail,
      password: signupPassword,
    });

    if (res.ok) {
      setMessage("Signup successful. You can now log in.");
      setSignupName("");
      setSignupEmail("");
      setSignupPassword("");
    } else {
      const text = await res.text();
      setMessage(`Signup failed: ${text}`);
    }
  }

  async function handleLogin() {
    setMessage(null);
    const form = new URLSearchParams();
    form.append("username", loginEmail);
    form.append("password", loginPassword);

    const res = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      const text = await res.text();
      setMessage(`Login failed: ${text}`);
      return;
    }

    const tokenData = await res.json(); // { access_token, token_type }
    const accessToken = tokenData.access_token as string;
    setToken(accessToken);

    // Fetch /me
    const meRes = await apiGet("/me", accessToken);
    if (!meRes.ok) {
      setMessage("Logged in but failed to fetch user info.");
      return;
    }
    const userJson = (await meRes.json()) as User;
    setUser(userJson);
    setTab("predict");
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
    setTab("auth");
    setPrediction(null);
    setPredictions([]);
    setFeedbacks([]);
    setHistoryLoaded(false);
  }

  // ========== PREDICTION HANDLERS ==========

  async function handlePredict() {
    setPredictMsg(null);
    setFbMsg(null);

    if (!file) {
      setPredictMsg("Please choose an image.");
      return;
    }
    if (!token) {
      setPredictMsg("Please log in first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const res = await apiPost("/predict", formData, token, true);
    if (!res.ok) {
      const text = await res.text();
      setPredictMsg(`Prediction failed: ${text}`);
      return;
    }

    const pred = (await res.json()) as Prediction;
    setPrediction(pred);
    setPredictMsg("Prediction complete!");
  }

  async function handleFeedbackSubmit() {
    if (!prediction || !token) return;

    const payload = {
      prediction_id: prediction.id,
      rating: fbRating,
      is_correct: fbCorrect === "yes",
      comment: fbComment || null,
    };

    const res = await apiPost("/feedback/", payload, token);
    if (res.ok) {
      setFbMsg("Feedback submitted. Thank you!");
    } else {
      const text = await res.text();
      setFbMsg(`Feedback failed: ${text}`);
    }
  }

  // ========== HISTORY HANDLER ==========

  async function loadHistory() {
    if (!token) return;
    setHistoryLoaded(false);

    const predsRes = await apiGet("/predictions/me", token);
    const fbRes = await apiGet("/feedback/me", token);

    if (predsRes.ok) {
      const predsJson = (await predsRes.json()) as Prediction[];
      setPredictions(predsJson);
    } else {
      setPredictions([]);
    }

    if (fbRes.ok) {
      const fbJson = (await fbRes.json()) as Feedback[];
      setFeedbacks(fbJson);
    } else {
      setFeedbacks([]);
    }

    setHistoryLoaded(true);
  }

  // ========== RENDER ==========

  // Logged-out view: show login/signup
  if (!token || !user || tab === "auth") {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 p-8">
        <div className="w-full max-w-xl rounded-xl bg-white p-8 shadow">
          <h1 className="mb-4 text-2xl font-semibold">
            Soybean Disease Prediction – Login / Signup
          </h1>
          {message && <p className="mb-4 text-red-600">{message}</p>}

          <section className="mb-8">
            <h2 className="mb-2 text-xl font-medium">Sign up</h2>
            <div className="flex flex-col gap-2">
              <input
                className="rounded border px-3 py-2"
                placeholder="Name"
                value={signupName}
                onChange={(e) => setSignupName(e.target.value)}
              />
              <input
                className="rounded border px-3 py-2"
                placeholder="Email"
                value={signupEmail}
                onChange={(e) => setSignupEmail(e.target.value)}
              />
              <input
                className="rounded border px-3 py-2"
                placeholder="Password"
                type="password"
                value={signupPassword}
                onChange={(e) => setSignupPassword(e.target.value)}
              />
              <button
                className="mt-2 rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700"
                onClick={handleSignup}
              >
                Sign up
              </button>
            </div>
          </section>

          <hr className="my-4" />

          <section>
            <h2 className="mb-2 text-xl font-medium">Log in</h2>
            <div className="flex flex-col gap-2">
              <input
                className="rounded border px-3 py-2"
                placeholder="Email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
              />
              <input
                className="rounded border px-3 py-2"
                placeholder="Password"
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
              <button
                className="mt-2 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                onClick={handleLogin}
              >
                Log in
              </button>
            </div>
          </section>
        </div>
      </main>
    );
  }

  // Logged-in view
  return (
    <main className="flex min-h-screen flex-col items-center bg-zinc-50 p-8">
      <div className="w-full max-w-4xl rounded-xl bg-white p-8 shadow">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">
              Soybean Disease Prediction
            </h1>
            <p className="text-sm text-zinc-600">Logged in as {user.name}</p>
          </div>
          <div className="flex gap-2">
            <button
              className={`rounded px-4 py-2 ${
                tab === "predict"
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-200 text-zinc-800"
              }`}
              onClick={() => setTab("predict")}
            >
              Predict
            </button>
            <button
              className={`rounded px-4 py-2 ${
                tab === "history"
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-200 text-zinc-800"
              }`}
              onClick={() => {
                setTab("history");
                void loadHistory();
              }}
            >
              History & Feedback
            </button>
            <button
              className="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </header>

        {tab === "predict" && (
          <section>
            <h2 className="mb-4 text-xl font-medium">Upload an image</h2>
            {predictMsg && (
              <p className="mb-2 text-sm text-zinc-700">{predictMsg}</p>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const f = e.target.files?.[0] || null;
                setFile(f);

                if (previewUrl) {
                  URL.revokeObjectURL(previewUrl);
                }
            
                if (f) {
                  const objectUrl = URL.createObjectURL(f);
                  setPreviewUrl(objectUrl);
                } else {
                  setPreviewUrl(null);
                }
              }}
              className="mb-2"
            />
            {previewUrl && (
              <div className="mt-4">
              <p className="mb-2 text-sm text-zinc-600">Preview of uploaded image:</p>
              <img
                src={previewUrl}
                alt="Uploaded soybean leaf"
                className="max-h-64 rounded border"
              />
            </div>
            )}
            <div>
              <button
                className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                onClick={handlePredict}
              >
                Run prediction
              </button>
            </div>
            
  
            {prediction && (
              <div className="mt-6 rounded border p-4">
                <h3 className="mb-2 text-lg font-semibold">
                  Prediction result
                </h3>
                <p>
                  <strong>Disease:</strong> {prediction.predicted_label}
                </p>
                <p>
                  <strong>Confidence:</strong>{" "}
                  {prediction.confidence !== null
                    ? prediction.confidence.toFixed(2)
                    : "N/A"}
                </p>
                <p>
                  <strong>Created at:</strong> {prediction.created_at}
                </p>

                <div className="mt-4">
                  <h4 className="mb-2 font-medium">
                    Was this prediction correct?
                  </h4>
                  <div className="mb-2 flex gap-4">
                    <label>
                      <input
                        type="radio"
                        checked={fbCorrect === "yes"}
                        onChange={() => setFbCorrect("yes")}
                      />{" "}
                      Yes
                    </label>
                    <label>
                      <input
                        type="radio"
                        checked={fbCorrect === "no"}
                        onChange={() => setFbCorrect("no")}
                      />{" "}
                      No
                    </label>
                  </div>
                  <div className="mb-2">
                    <label>
                      Rating (1–5):{" "}
                      <input
                        type="number"
                        min={1}
                        max={5}
                        value={fbRating}
                        onChange={(e) =>
                          setFbRating(Number(e.target.value) || 1)
                        }
                        className="w-16 rounded border px-2 py-1"
                      />
                    </label>
                  </div>
                  <div className="mb-2">
                    <textarea
                      className="w-full rounded border px-3 py-2"
                      placeholder="Comments..."
                      value={fbComment}
                      onChange={(e) => setFbComment(e.target.value)}
                    />
                  </div>
                  <button
                    className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700"
                    onClick={handleFeedbackSubmit}
                  >
                    Submit feedback
                  </button>
                  {fbMsg && (
                    <p className="mt-2 text-sm text-zinc-700">{fbMsg}</p>
                  )}
                </div>
              </div>
            )}
          </section>
        )}

        {tab === "history" && (
          <section className="flex gap-6">
            <div className="flex-1">
              <h2 className="mb-2 text-xl font-medium">Your predictions</h2>
              {!historyLoaded && <p>Loading...</p>}
              {historyLoaded && predictions.length === 0 && (
                <p>No predictions yet.</p>
              )}
              {historyLoaded &&
                predictions.map((p) => (
                  <div
                    key={p.id}
                    className="mb-3 rounded border p-3 text-sm"
                  >
                    <p>
                      <strong>ID:</strong> {p.id}
                    </p>
                    <p>
                      <strong>Disease:</strong> {p.predicted_label} (conf:{" "}
                      {p.confidence !== null
                        ? p.confidence.toFixed(2)
                        : "N/A"}
                      )
                    </p>
                    <p>
                      <strong>Image:</strong> {p.image_url}
                    </p>
                    <p>
                      <strong>Created at:</strong> {p.created_at}
                    </p>
                  </div>
                ))}
            </div>
            <div className="flex-1">
              <h2 className="mb-2 text-xl font-medium">Your feedback</h2>
              {!historyLoaded && <p>Loading...</p>}
              {historyLoaded && feedbacks.length === 0 && (
                <p>No feedback yet.</p>
              )}
              {historyLoaded &&
                feedbacks.map((fb) => (
                  <div
                    key={fb.id}
                    className="mb-3 rounded border p-3 text-sm"
                  >
                    <p>
                      <strong>Prediction ID:</strong> {fb.prediction_id}
                    </p>
                    <p>
                      <strong>Rating:</strong> {fb.rating ?? "N/A"}
                    </p>
                    <p>
                      <strong>Correct?:</strong>{" "}
                      {fb.is_correct === null
                        ? "N/A"
                        : fb.is_correct
                        ? "Yes"
                        : "No"}
                    </p>
                    <p>
                      <strong>Comment:</strong> {fb.comment ?? ""}
                    </p>
                    <p>
                      <strong>Created at:</strong> {fb.created_at}
                    </p>
                  </div>
                ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
