import { useState } from 'react';

type JSONPrimitive = string | number | boolean | null;
export type JSONValue = JSONPrimitive | readonly JSONValue[] | { readonly [key: string]: JSONValue };

interface JSONViewerProps {
  readonly data: JSONValue;
}

const isJsonArray = (value: JSONValue): value is readonly JSONValue[] => Array.isArray(value);

const isJsonRecord = (value: JSONValue): value is { readonly [key: string]: JSONValue } => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
);

export const JSONViewer = ({ data }: JSONViewerProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const isArray = isJsonArray(data);
  const isObject = isJsonRecord(data);

  const toggleCollapse = () => setIsCollapsed((current) => !current);

  const renderValue = (value: JSONValue) => {
    if (typeof value === 'string') {
      return <span className="text-[var(--color-success)]">&quot;{value}&quot;</span>;
    }
    if (typeof value === 'number') {
      return <span className="text-[var(--color-info)]">{value}</span>;
    }
    if (typeof value === 'boolean') {
      return <span className="text-[var(--color-primary)]">{value.toString()}</span>;
    }
    if (value === null) {
      return <span className="text-[var(--color-text-muted)]">null</span>;
    }
    return <JSONViewer data={value} />;
  };

  if (!isArray && !isObject) {
    return <div className="font-mono text-sm">{renderValue(data)}</div>;
  }

  return (
    <div className="font-mono text-sm">
      <div className="flex items-start">
        <button
          type="button"
          onClick={toggleCollapse}
          className="flex cursor-pointer items-center gap-1 rounded px-2 py-0.5 transition-colors hover:bg-[color-mix(in_srgb,var(--color-primary)_9%,var(--color-card))] group"
        >
          <svg
            className={`h-3 w-3 text-[var(--color-primary)] transition-transform ${isCollapsed ? '' : 'rotate-90'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-[var(--color-text-muted)] transition-colors group-hover:text-[var(--color-text)]">
            {isArray ? '[' : '{'}
          </span>
        </button>
      </div>

      {!isCollapsed ? (
        <div className="ml-5 border-l-2 border-[color-mix(in_srgb,var(--color-primary)_26%,var(--color-border))] py-1 pl-4">
          {isArray ? data.map((item, index) => (
            <div key={index} className="my-1.5">
              <span className="font-semibold text-[var(--color-info)]">{index}</span>
              <span className="text-[var(--color-text-muted)]">: </span>
              {renderValue(item)}
            </div>
          )) : null}

          {isObject ? Object.entries(data).map(([key, value]) => (
            <div key={key} className="my-1.5">
              <span className="font-medium text-[var(--color-primary)]">&quot;{key}&quot;</span>
              <span className="text-[var(--color-text-muted)]">: </span>
              {renderValue(value)}
            </div>
          )) : null}
        </div>
      ) : null}

      <div className="flex items-center">
        <button type="button" className="cursor-pointer text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text)]" onClick={toggleCollapse}>
          {isArray ? ']' : '}'}
        </button>
      </div>
    </div>
  );
};
