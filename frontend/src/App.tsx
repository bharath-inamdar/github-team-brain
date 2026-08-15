import { AuthProvider, useAuth } from "@/auth/AuthContext";
import AuthPage from "@/pages/AuthPage";
import Dashboard from "@/pages/Dashboard";

function AuthGate() {
  const { user, initializing } = useAuth();

  if (initializing) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f7f8fb] text-slate-500">
        <div className="text-sm">Loading TeamBrain...</div>
      </main>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <Dashboard />;
}

function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
}

export default App;
