export default function StarRating({ stars, maxStars = 5 }) {
  return (
    <div className="flex items-center gap-1" role="img" aria-label={`${stars} out of ${maxStars} stars`}>
      {Array.from({ length: maxStars }).map((_, i) => (
        <svg
          key={i}
          viewBox="0 0 20 20"
          className={`h-5 w-5 ${i < stars ? 'text-[var(--color-indigo)]' : 'text-[var(--color-line)]'}`}
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M10 1.5l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6-4.5-4.2 6.1-.7L10 1.5z" />
        </svg>
      ))}
    </div>
  )
}
