import axios from "axios";

const API_URL = "http://127.0.0.1:5000";

export const getPlayers = async () => {
    try {
        const response = await axios.get(`${API_URL}/players`);
        return response.data;
    } catch (error) {
        console.error("Error fetching players:", error);
        return [];
    }
};

export const getTrainingRoutine = async (playerId) => {
    try {
        const response = await axios.get(`${API_URL}/training/${playerId}`);
        return response.data;
    } catch (error) {
        console.error("Error fetching training routine:", error);
        return {};
    }
};
