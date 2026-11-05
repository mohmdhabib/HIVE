import { createClient } from "@supabase/supabase-js";

const supabaseUrl = (import.meta as any).env?.VITE_SUPABASE_URL || "https://bksoqxewamrqnqjqborx.supabase.co";
const supabaseKey = (import.meta as any).env?.VITE_SUPABASE_PUBLISHABLE_KEY || "sb_publishable_Pw1yZskOS_4B15_fFkrhBA_5TryJ-9L";

export const supabase = createClient(supabaseUrl, supabaseKey);
