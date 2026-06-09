import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Session, User } from "@supabase/supabase-js";
import { signUpAccount } from "../api/auth";
import * as facultyApi from "../api/faculty";
import * as studentApi from "../api/student";
import { getSupabase, type Portal } from "../lib/supabase";

export type UserRole = "student" | "faculty" | "admin";

type SignUpData = {
  email: string;
  password: string;
  fullName: string;
  role: UserRole;
  enrollmentId?: string;
  semester?: string;
  branch?: string;
};

type UserProfile = facultyApi.UserProfile;

type AuthContextValue = {
  portal: Portal;
  session: Session | null;
  user: User | null;
  profile: UserProfile | null;
  profileError: string | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (data: SignUpData) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  portal,
  children,
}: {
  portal: Portal;
  children: ReactNode;
}) {
  const supabase = getSupabase(portal);
  const defaultRole: UserRole = portal === "faculty" ? "faculty" : "student";
  const fetchProfile =
    portal === "faculty" ? facultyApi.fetchProfile : studentApi.fetchProfile;

  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    const currentSession = (await supabase.auth.getSession()).data.session;
    if (!currentSession?.access_token) {
      setProfile(null);
      setProfileError(null);
      return;
    }
    try {
      const data = await fetchProfile(currentSession.access_token);
      setProfile(data);
      setProfileError(null);
    } catch (err) {
      setProfile(null);
      setProfileError(err instanceof Error ? err.message : "Failed to load profile");
    }
  }, [fetchProfile, supabase]);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => listener.subscription.unsubscribe();
  }, [supabase]);

  useEffect(() => {
    if (!session?.access_token) {
      setProfile(null);
      return;
    }
    refreshProfile().catch(() => undefined);
  }, [session?.access_token, refreshProfile]);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
    },
    [supabase],
  );

  const signUp = useCallback(
    async (data: SignUpData) => {
      await signUpAccount({
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        role: data.role === "faculty" ? "faculty" : "student",
        enrollment_id: data.enrollmentId,
        semester: data.semester,
        branch: data.branch,
      });
      const { error } = await supabase.auth.signInWithPassword({
        email: data.email,
        password: data.password,
      });
      if (error) throw error;
    },
    [supabase],
  );

  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/${portal}` },
    });
    if (error) throw error;
  }, [portal, supabase]);

  const signOut = useCallback(async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    setProfile(null);
  }, [supabase]);

  const value = useMemo(
    () => ({
      portal,
      session,
      user: session?.user ?? null,
      profile,
      profileError,
      loading,
      signIn,
      signUp: (data: SignUpData) =>
        signUp({ ...data, role: data.role ?? defaultRole }),
      signInWithGoogle,
      signOut,
      refreshProfile,
    }),
    [
      portal,
      session,
      profile,
      profileError,
      loading,
      signIn,
      signUp,
      defaultRole,
      signInWithGoogle,
      signOut,
      refreshProfile,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
