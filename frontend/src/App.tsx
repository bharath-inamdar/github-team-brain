import Header from "./components/Header";
import SummaryCard from "./components/SummaryCard";

function App() {
  return (
    <div className="min-h-screen bg-slate-100">
      <main className="max-w-5xl mx-auto px-6 py-10">
        <Header />
        <SummaryCard />
      </main>
    </div>
  );
}

export default App;