import type { FormControlProps } from '@chakra-ui/react';
import type { UseFormRegister } from 'react-hook-form';
import type { OnChangeArgs, FormData, SingleOption } from '~/types';

export interface TField extends FormControlProps {
  name: string;
  label: string;
  hiddenLabels?: boolean;
  labelAddOn?: React.ReactNode;
  fieldAddOn?: React.ReactNode;
}

export type OnChange = (f: OnChangeArgs) => void;

export interface TQuerySelectField {
  onChange: OnChange;
  label: string;
}

export interface TQueryTarget {
  name: string;
  placeholder: string;
  register: UseFormRegister<FormData>;
  onChange(e: OnChangeArgs): void;
}

export interface ResolvedTargetProps {
  errorClose(): void;
}

export interface LocationCardProps {
  option: SingleOption;
  defaultChecked: boolean;
  onChange(a: 'add' | 'remove', v: SingleOption): void;
  hasError: boolean;
}
