import React, { useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5000"; 

function PlayerAssessment() {
  const [formData, setFormData] = useState({
    name: "",
    position: "",
    shooting_accuracy: "",
    dribbling_skill: "",
    finishing_skill: "",
  });

  const [response, setResponse] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API_URL}/assess_player`, formData);
      setResponse(res.data.message);
    } catch (error) {
      setResponse("Error adding player.");
    }
  };

  return (
    <div>
      <h2>🏀 Player Skill Assessment</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="name"
          placeholder="Player Name"
          onChange={handleChange}
          required
        />
        <select name="position" onChange={handleChange} required>
          <option value="">Select Position</option>
          <option value="Guard">Guard</option>
          <option value="Forward">Forward</option>
          <option value="Center">Center</option>
        </select>
        <input
          type="number"
          name="shooting_accuracy"
          placeholder="Shooting Accuracy (0-100)"
          onChange={handleChange}
          required
        />
        <input
          type="number"
          name="dribbling_skill"
          placeholder="Dribbling Skill (0-100)"
          onChange={handleChange}
          required
        />
        <input
          type="number"
          name="finishing_skill"
          placeholder="Finishing at the Rim (0-100)"
          onChange={handleChange}
          required
        />
        <button type="submit">Assess Player</button>
      </form>
      {response && <p>{response}</p>}
    </div>
  );
}

export default PlayerAssessment;
