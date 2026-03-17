import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabase";

type SignupForm = {
  username: string;
  email: string;
  password: string;
};

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<SignupForm>({
    username: "",
    email: "",
    password: "",
  });

  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!form.username || !form.email || !form.password) {
      setError("All fields are required");
      return;
    }

    setError("");
    setIsSubmitting(true);

    const { data, error: signUpError } = await supabase.auth.signUp({
      email: form.email,
      password: form.password,
      options: {
        data: {
          username: form.username,
          full_name: form.username,
        },
      },
    });

    if (signUpError) {
      setError(signUpError.message);
      setIsSubmitting(false);
      return;
    }

    if (data.session) {
      let navigated = false;
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((event) => {
        if (event !== "SIGNED_OUT" || navigated) return;

        navigated = true;
        subscription.unsubscribe();
        setIsSubmitting(false);
        navigate("/login", {
          replace: true,
          state: { signupSuccess: true },
        });
      });

      const { error: signOutError } = await supabase.auth.signOut();

      if (signOutError) {
        subscription.unsubscribe();
        setError(signOutError.message);
        setIsSubmitting(false);
        return;
      }

      window.setTimeout(() => {
        if (navigated) return;

        navigated = true;
        subscription.unsubscribe();
        setIsSubmitting(false);
        navigate("/login", {
          replace: true,
          state: { signupSuccess: true },
        });
      }, 300);
      return;
    }

    setIsSubmitting(false);
    navigate("/login", {
      replace: true,
      state: { signupSuccess: true },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4">
      
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
        
        <h2 className="text-2xl font-bold text-center mb-6">
          Create Account
        </h2>

        {error && (
          <div className="mb-4 text-sm text-red-500 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Username
            </label>

            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Enter username"
              autoComplete="username"
              className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email
            </label>

            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Enter email"
              autoComplete="email"
              className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Password
            </label>

            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter password"
              autoComplete="new-password"
              className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          {/* Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-slate-900 text-white py-2 rounded-lg hover:bg-slate-800 transition"
          >
            {isSubmitting ? "Signing up..." : "Sign Up"}
          </button>

        </form>

        <p className="text-sm text-center mt-4 text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="text-slate-900 font-medium hover:underline">
            Login
          </Link>
        </p>

      </div>
    </div>
  );
}
