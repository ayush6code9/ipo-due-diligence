export default function SuggestedQuestions({ questions, onPick }) {
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q) => (
        <button
          key={q}
          type="button"
          onClick={() => onPick(q)}
          className="text-xs font-medium text-[var(--color-ink-soft)] bg-[var(--color-line-soft)]
            hover:bg-[var(--color-indigo-soft)] hover:text-[var(--color-indigo)] hover:border-[var(--color-indigo)]/30
            border border-[var(--color-line)] rounded-full px-3 py-1.5 transition-all text-left"
        >
          {q}
        </button>
      ))}
    </div>
  )
}
