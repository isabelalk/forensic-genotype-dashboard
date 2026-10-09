import type { ComponentType, ReactNode } from 'react';
import {
  HiOutlineCheckCircle,
  HiOutlineExclamationCircle,
  HiOutlineInformationCircle,
  HiOutlineXCircle,
} from 'react-icons/hi';

type AlertVariant = 'success' | 'warning' | 'error' | 'info';

interface AlertProps {
  readonly variant: AlertVariant;
  readonly children: ReactNode;
  readonly icon?: ComponentType<{ readonly className?: string }>;
}

const variantStyles: Record<AlertVariant, {
  readonly container: string;
  readonly icon: string;
}> = {
  success: {
    container: 'border-[color-mix(in_srgb,var(--color-success)_38%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))]',
    icon: 'text-[var(--color-success)]',
  },
  warning: {
    container: 'border-[color-mix(in_srgb,var(--color-warning)_40%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))]',
    icon: 'text-[var(--color-warning)]',
  },
  error: {
    container: 'border-[color-mix(in_srgb,var(--color-error)_40%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-error)_10%,var(--color-card))]',
    icon: 'text-[var(--color-error)]',
  },
  info: {
    container: 'border-[color-mix(in_srgb,var(--color-info)_34%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))]',
    icon: 'text-[var(--color-info)]',
  },
};

const defaultIcons: Record<AlertVariant, ComponentType<{ readonly className?: string }>> = {
  success: HiOutlineCheckCircle,
  warning: HiOutlineExclamationCircle,
  error: HiOutlineXCircle,
  info: HiOutlineInformationCircle,
};

export const Alert = ({ variant, children, icon }: AlertProps) => {
  const DisplayIcon = icon ?? defaultIcons[variant];
  const styles = variantStyles[variant];

  return (
    <div className={`relative rounded-2xl border p-5 shadow-[var(--shadow-card)] animate-slide-up ${styles.container}`}>
      <div className="flex items-start gap-4">
        <DisplayIcon className={`h-6 w-6 flex-shrink-0 ${styles.icon}`} />
        <div className="flex-1 text-[var(--color-text)]">{children}</div>
      </div>
    </div>
  );
};
