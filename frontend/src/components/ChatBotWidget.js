import React, { useState } from "react";
import "./ChatBotWidget.css";

function ChatBotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hey! I'm here to answer your basketball questions." }
  ]);
  const [input, setInput] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");

    try {
      // 🏀 Check if it's an NBA stat request
      if (input.toLowerCase().includes("stats for")) {
        const playerName = input.replace(/stats for/i, "").trim();
        const res = await fetch("http://127.0.0.1:5000/nba_stats", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ player: playerName }),
        });
        const data = await res.json();
        setMessages([...newMessages, { sender: "bot", text: data.response || data.error }]);
        return;
      }

      // 🤖 Otherwise ask GPT
      const res = await fetch("http://127.0.0.1:5000/faq_bot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();
      setMessages([...newMessages, { sender: "bot", text: data.response }]);
    } catch (err) {
      setMessages([
        ...newMessages,
        { sender: "bot", text: "❌ Something went wrong. Please try again later." },
      ]);
    }
  };

  return (
    <div className="chatbot-container">
      {open && (
        <div className="chatbox">
          <div className="chat-header">🤖 FAQ Bot</div>
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
          </div>
          <div className="chat-input-vertical">
            <input
              type="text"
              placeholder="Ask something..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      )}
      <button className="chat-toggle" onClick={() => setOpen(!open)}>
        {open ? "✖" : "💬 FAQ"}
      </button>
    </div>
  );
}

export default ChatBotWidget;
