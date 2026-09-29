export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-4 py-16">
      <h1 className="text-4xl font-semibold tracking-tight">
        GrahRekha <span className="text-2xl font-normal text-zinc-500">ग्रह-रेखा</span>
      </h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-300">
        Planets in your palm, lines in your stars. An open-source research project on AI-assisted
        palmistry (Hast Rekha) and Vedic astrology.
      </p>
      <p className="text-sm text-zinc-500">
        Work in progress (Phase 0). For entertainment and self-reflection only — no health,
        lifespan or medical claims.{" "}
        <a className="underline" href="https://github.com/atultiwari/grahrekha">
          Source on GitHub
        </a>
      </p>
    </main>
  );
}
