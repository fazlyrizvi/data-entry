import React, { useMemo } from 'react'
import EChartsReact from 'echarts-for-react'

export const ErrorRateChart: React.FC = () => {
  const option = useMemo(() => ({
    title: {
      text: 'Error Rate Trends',
      left: 'left',
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
        color: '#171717'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(0, 0, 0, 0.1)',
      textStyle: {
        color: '#171717'
      }
    },
    legend: {
      data: ['Errors', 'Warnings', 'Success Rate'],
      top: 'bottom',
      textStyle: {
        color: '#A3A3A3',
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      axisLine: {
        lineStyle: {
          color: '#E5E5E5'
        }
      },
      axisLabel: {
        color: '#A3A3A3'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#E5E5E5'
        }
      },
      axisLabel: {
        color: '#A3A3A3',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: '#F5F5F5'
        }
      }
    },
    series: [
      {
        name: 'Errors',
        type: 'line',
        data: [2.1, 1.8, 2.3, 1.5, 1.9, 1.2, 0.8],
        lineStyle: {
          color: '#EF4444',
          width: 2
        },
        itemStyle: {
          color: '#EF4444'
        }
      },
      {
        name: 'Warnings',
        type: 'line',
        data: [3.2, 2.8, 3.5, 2.9, 3.1, 2.4, 2.1],
        lineStyle: {
          color: '#F59E0B',
          width: 2
        },
        itemStyle: {
          color: '#F59E0B'
        }
      },
      {
        name: 'Success Rate',
        type: 'line',
        data: [94.7, 95.4, 94.2, 95.6, 95.0, 96.4, 97.1],
        lineStyle: {
          color: '#10B981',
          width: 3
        },
        itemStyle: {
          color: '#10B981'
        }
      }
    ]
  }), [])

  return (
    <div className="h-80">
      <EChartsReact
        option={option}
        style={{ height: '100%', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}