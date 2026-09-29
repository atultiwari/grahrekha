import { z } from "zod";

const EnvSchema = z.object({
  ENGINE_URL: z.string().url("ENGINE_URL must be a valid URL").default("http://localhost:8000"),
  ENGINE_SHARED_SECRET: z
    .string({ required_error: "ENGINE_SHARED_SECRET is required (see .env.example)" })
    .min(1, "ENGINE_SHARED_SECRET must not be empty"),
});

export interface ServerConfig {
  engineUrl: string;
  engineSecret: string;
}

/** Validates server-side environment variables. Throws with a readable message on problems. */
export function loadServerConfig(env: Record<string, string | undefined> = process.env): ServerConfig {
  const parsed = EnvSchema.safeParse(env);
  if (!parsed.success) {
    const problems = parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; ");
    throw new Error(`Invalid server configuration — ${problems}`);
  }
  return { engineUrl: parsed.data.ENGINE_URL, engineSecret: parsed.data.ENGINE_SHARED_SECRET };
}
