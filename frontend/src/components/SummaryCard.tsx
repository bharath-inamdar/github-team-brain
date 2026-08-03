import { useState } from "react";
import api from "../services/api";
import ReactMarkdown from "react-markdown";

function SummaryCard() {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const generateSummary = async () => {
    try {
      setLoading(true);
      setErrorMessage("");

      const response = await api.get("/ai/repository-summary");

      setSummary(response.data.summary);
    } catch {
      setErrorMessage("Failed to generate summary. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mt-6">
      <h2 className="text-xl font-semibold mb-4">
        📄 Repository Summary
      </h2>

      <button
        onClick={generateSummary}
        disabled={loading}
        className="
          bg-blue-600
          hover:bg-blue-700
          text-white
          px-5
          py-2
          rounded-lg
          transition
          disabled:bg-gray-400
        "
      >
        {loading ? "Generating..." : "Generate Summary"}
      </button>

      {errorMessage && (
        <p className="mt-4 text-sm text-red-600">
          {errorMessage}
        </p>
      )}

      {summary && (
        <div className="markdown mt-6">
          <ReactMarkdown>
            {summary}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}

export default SummaryCard;
