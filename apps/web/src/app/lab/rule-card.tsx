import type { FiredRuleV1 } from "@grahrekha/contracts";

/** One fired rule with its statement, citation and any known measurement issue. */
export function RuleCard({ rule }: { rule: FiredRuleV1 }) {
  return (
    <li className="rounded-md border p-3">
      <p>{rule.statement.en}</p>
      <details className="mt-2 text-xs text-zinc-600 dark:text-zinc-400">
        <summary className="cursor-pointer">
          Why? <code>{rule.id}</code> · {rule.status}
        </summary>
        <p className="mt-1">
          {rule.source.work}, {rule.source.locator}
        </p>
        {rule.source.quote && <blockquote className="mt-1 border-l-2 pl-2 italic">{rule.source.quote}</blockquote>}
        {rule.mapping_note && <p className="mt-1">Mapping: {rule.mapping_note}</p>}
      </details>
      {rule.validity_blocker && (
        <p className="mt-2 rounded bg-red-50 p-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200">
          Known measurement issue: {rule.validity_blocker}
        </p>
      )}
    </li>
  );
}
