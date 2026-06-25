export function PageHeader({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <section className="border-b border-brand-100 bg-brand-50/50">
      <div className="mx-auto max-w-4xl px-5 py-16 text-center sm:px-8">
        {eyebrow && (
          <span className="badge">{eyebrow}</span>
        )}
        <h1 className="mt-4 font-serif text-4xl font-extrabold text-brand-800 sm:text-5xl">
          {title}
        </h1>
        {subtitle && (
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
            {subtitle}
          </p>
        )}
      </div>
    </section>
  );
}
