/**
 * Пример интеграции React + Telegram WebApp → Django POST /api/auth/
 *
 * 1. В index.html подключите скрипт (до вашего бандла):
 *    <script src="https://telegram.org/js/telegram-web-app.js"></script>
 *
 * 2. Укажите URL бэкенда (тот же хост или прокси с CORS).
 */
import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export function WebAppAuthExample() {
  const [status, setStatus] = useState("idle");
  const [userId, setUserId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) {
      setError("Откройте приложение из Telegram (WebApp недоступен)");
      return;
    }
    tg.ready();
    tg.expand();

    const user = tg.initDataUnsafe?.user;
    if (!user || !tg.initData) {
      setError("Нет данных пользователя или initData");
      return;
    }

    const payload = {
      init_data: tg.initData,
      user: {
        id: user.id,
        first_name: user.first_name ?? "",
        last_name: user.last_name ?? "",
        username: user.username ?? null,
      },
    };

    setStatus("loading");
    fetch(`${API_BASE}/api/auth/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(JSON.stringify(data));
        setUserId(data.user_id);
        setStatus("ok");
      })
      .catch((e) => {
        setError(String(e.message ?? e));
        setStatus("error");
      });
  }, []);

  return (
    <div>
      <p>Статус: {status}</p>
      {userId != null && <p>user_id: {userId}</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}
