import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1",
  headers: {
    "X-API-Key": "4d3e9d7a8f9c12b45e6f7g8h9i0jklmn",
  },
});

export default api;