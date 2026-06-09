import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export type Portal = "faculty" | "student";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";

const clients: Partial<Record<Portal, SupabaseClient>> = {};

/** Separate auth storage per portal so faculty + student can stay logged in in parallel tabs. */
export function getSupabase(portal: Portal): SupabaseClient {
  if (!clients[portal]) {
    clients[portal] = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        storageKey: `acadmind-auth-${portal}`,
      },
    });
  }
  return clients[portal]!;
}
