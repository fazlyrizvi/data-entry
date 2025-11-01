import React from 'react'
import { cn } from '../../lib/utils'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  padding?: 'sm' | 'md' | 'lg'
  onClick?: () => void
}

export const GlassCard: React.FC<GlassCardProps> = ({ 
  children, 
  className, 
  hover = true,
  padding = 'lg',
  onClick 
}) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  }

  return (
    <div
      className={cn(
        'rounded-lg border border-glass-border bg-glass-light backdrop-blur-glass shadow-glass',
        hover && 'transition-all duration-300 hover:shadow-card-hover hover:-translate-y-1 cursor-pointer',
        paddingClasses[padding],
        onClick && 'hover:bg-glass-lightHover',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: string | number
  change?: {
    value: number
    type: 'increase' | 'decrease'
  }
  icon?: React.ComponentType<{ className?: string }>
  className?: string
}

export const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  change, 
  icon: Icon,
  className 
}) => {
  return (
    <GlassCard className={className}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-neutral-700 mb-2">{title}</p>
          <p className="text-3xl font-bold text-neutral-900 mb-1">{value}</p>
          {change && (
            <p className={cn(
              'text-sm flex items-center',
              change.type === 'increase' ? 'text-semantic-success' : 'text-semantic-error'
            )}>
              <span className="mr-1">
                {change.type === 'increase' ? '↗' : '↘'}
              </span>
              {Math.abs(change.value)}%
            </p>
          )}
        </div>
        {Icon && (
          <div className="ml-4">
            <Icon className="w-8 h-8 text-primary-500" />
          </div>
        )}
      </div>
    </GlassCard>
  )
}

interface StatusCardProps {
  title: string
  description: string
  status: 'success' | 'warning' | 'error' | 'info'
  progress?: number
  icon?: React.ComponentType<{ className?: string }>
}

export const StatusCard: React.FC<StatusCardProps> = ({ 
  title, 
  description, 
  status, 
  progress,
  icon: Icon 
}) => {
  const statusColors = {
    success: 'text-semantic-success',
    warning: 'text-semantic-warning',
    error: 'text-semantic-error',
    info: 'text-semantic-info'
  }

  const progressColor = {
    success: 'bg-semantic-success',
    warning: 'bg-semantic-warning',
    error: 'bg-semantic-error',
    info: 'bg-semantic-info'
  }

  return (
    <GlassCard>
      <div className="flex items-start space-x-4">
        {Icon && (
          <div className="flex-shrink-0">
            <Icon className={cn('w-8 h-8', statusColors[status])} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-xl font-semibold text-neutral-900 mb-1">{title}</p>
          <p className="text-sm text-neutral-600 mb-3">{description}</p>
          {progress !== undefined && (
            <div className="space-y-2">
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div 
                  className={cn('h-2 rounded-full transition-all duration-300', progressColor[status])}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-neutral-500">{progress}% complete</p>
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  )
}