import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import type { Session } from "@supabase/supabase-js";
import JobIntakeForm from "./components/JobIntakeForm";
import LoginPage from "./components/LoginPage";
import SignupPage from "./components/SignupPage";
import { supabase } from "./lib/supabase";

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    void supabase.auth.getSession().then(({ data }) => {
      if (!isMounted) return;
      setSession(data.session);
      setAuthLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, []);

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
        <div className="text-sm font-medium text-slate-600">Checking session...</div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to={session ? "/intake" : "/login"} replace />} />
      <Route path="/login" element={session ? <Navigate to="/intake" replace /> : <LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/intake" element={session ? <JobIntakeForm /> : <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to={session ? "/intake" : "/login"} replace />} />
    </Routes>
  );
}

export default App;
