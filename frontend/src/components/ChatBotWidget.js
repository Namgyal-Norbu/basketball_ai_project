import React, { useState, useEffect, useRef } from "react";
import "./ChatBotWidget.css";
import { auth } from "../firebaseConfig";
 
// setting different categories
const categories = [
  "📋 Daily Drills",
  "📈 Player Progress",
  "🎖️ Achievements & Badges",
  "🎯 Leveling & XP",
  "📅 Training Schedule",
  "🏆 Leaderboard Info",
  "🛠️ Account & Settings",
];
// subcategories
const subcategories = {
  "📋 Daily Drills": ["Today's Drills"],
  "📈 Player Progress": ["XP", "Skill Level", "Progress Graph"],
  "🎖️ Achievements & Badges": ["My Badges"],
  "🎯 Leveling & XP": ["How do I earn XP?"],
  "📅 Training Schedule": ["Recommended Weekly Routine"],
  "🏆 Leaderboard Info": ["Top Players"],
  "🛠️ Account & Settings": ["Delete My Profile", "Export My Data"],
};

function
 ChatBotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hey! I'm here to answer your basketball questions." },
  ]);
  const [stage, setStage] = useState("category");
  const [selectedCategory, setSelectedCategory] = useState("");

  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, stage]);

  const addMessage = (sender, text) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  const handleCategorySelect = (category) => {
    addMessage("user", category);
    setSelectedCategory(category);
    setStage("subcategory");

    setTimeout(() => {
      addMessage("bot", "Great! What do you want to know about?");
    }, 400);
  };

  const handleSubcategorySelect = async (sub) => {
    addMessage("user", sub);
    const user = auth.currentUser;
    const email = user?.email || null;

    try {
      const res = await fetch("http://127.0.0.1:5050/chatbot_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: selectedCategory,
          subcategory: sub.toLowerCase().replace(/[^a-z0-9]/gi, ""),
          email,
        }),
      });

      const data = await res.json();
      addMessage("bot", data.response);
    } catch (err) {
      addMessage("bot", "❌ Sorry, something went wrong.");
    }

    setStage("done");
  };

  const resetChat = () => {
    setStage("category");
    setSelectedCategory("");
    addMessage("bot", "What else would you like to ask?");
  };

  return (
    <div className="chatbot-container">
      {open && (
        <div className="chatbox">
          <div className="chat-header">🤖 Basketball ChatBot</div>

          <div className="chat-scroll-wrapper" ref={scrollRef}>
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.sender}`}>
                  {msg.text}
                </div>
              ))}

              {stage === "category" &&
                categories.map((cat) => (
                  <button
                    className="chat-button"
                    key={cat}
                    onClick={() => handleCategorySelect(cat)}
                  >
                    {cat}
                  </button>
                ))}

              {stage === "subcategory" &&
                subcategories[selectedCategory].map((sub) => (
                  <button
                    className="chat-button"
                    key={sub}
                    onClick={() => handleSubcategorySelect(sub)}
                  >
                    {sub}
                  </button>
                ))}

              {stage === "done" && (
                <button className="chat-button" onClick={resetChat}>
                  🔄 Ask Another Question
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <button className="chat-toggle" onClick={() => setOpen(!open)}>
        {open ? "✖" : "💬 Chat"}
      </button>
    </div>
  );
}

export default ChatBotWidget;
