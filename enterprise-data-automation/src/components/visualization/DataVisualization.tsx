import React from 'react'
import ReactECharts from 'echarts-for-react'

interface DataVisualizationProps {
  data: any[]
  dataSummary: any
}

export const DataVisualization: React.FC<DataVisualizationProps> = ({ data, dataSummary }) => {
  if (!data || data.length === 0) return null

  // Generate chart options based on data
  const getChartOptions = () => {
    const columns = dataSummary?.columns || {}
    const numericColumns = Object.entries(columns)
      .filter(([key, value]: [string, any]) => value.dataType === 'numeric')
      .map(([key]) => key)

    // If we have numeric data, create charts
    if (numericColumns.length > 0) {
      const firstNumericColumn = numericColumns[0]
      const values = data.map(row => parseFloat(row[firstNumericColumn]) || 0)

      return {
        bar: {
          title: {
            text: `${firstNumericColumn} Distribution`,
            left: 'center',
            textStyle: { fontSize: 14, fontWeight: 600 }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
          },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: {
            type: 'category',
            data: data.slice(0, 20).map((_, idx) => `Row ${idx + 1}`)
          },
          yAxis: { type: 'value' },
          series: [{
            name: firstNumericColumn,
            type: 'bar',
            data: values.slice(0, 20),
            itemStyle: {
              color: '#3B82F6',
              borderRadius: [4, 4, 0, 0]
            }
          }]
        },
        line: {
          title: {
            text: `${firstNumericColumn} Trend`,
            left: 'center',
            textStyle: { fontSize: 14, fontWeight: 600 }
          },
          tooltip: {
            trigger: 'axis'
          },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: {
            type: 'category',
            data: data.slice(0, 20).map((_, idx) => `${idx + 1}`)
          },
          yAxis: { type: 'value' },
          series: [{
            name: firstNumericColumn,
            type: 'line',
            smooth: true,
            data: values.slice(0, 20),
            lineStyle: { color: '#3B82F6', width: 2 },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                  { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
                ]
              }
            }
          }]
        }
      }
    }

    // For categorical data, create pie chart
    const firstColumn = Object.keys(data[0] || {})[0]
    if (firstColumn) {
      const categoryCounts: Record<string, number> = {}
      data.forEach(row => {
        const value = String(row[firstColumn])
        categoryCounts[value] = (categoryCounts[value] || 0) + 1
      })

      const pieData = Object.entries(categoryCounts).map(([name, value]) => ({
        name,
        value
      }))

      return {
        pie: {
          title: {
            text: `${firstColumn} Distribution`,
            left: 'center',
            textStyle: { fontSize: 14, fontWeight: 600 }
          },
          tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            top: 'middle'
          },
          series: [{
            name: firstColumn,
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 8,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold'
              }
            },
            data: pieData.slice(0, 10)
          }]
        }
      }
    }

    return null
  }

  const chartOptions = getChartOptions()

  if (!chartOptions) {
    return null
  }

  return (
    <div className="space-y-6">
      <h4 className="font-medium text-neutral-700 mb-4">Data Visualizations</h4>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {chartOptions.bar && (
          <div className="bg-white p-4 rounded-lg border border-neutral-200">
            <ReactECharts 
              option={chartOptions.bar} 
              style={{ height: '300px' }}
              opts={{ renderer: 'canvas' }}
            />
          </div>
        )}
        
        {chartOptions.line && (
          <div className="bg-white p-4 rounded-lg border border-neutral-200">
            <ReactECharts 
              option={chartOptions.line} 
              style={{ height: '300px' }}
              opts={{ renderer: 'canvas' }}
            />
          </div>
        )}
        
        {chartOptions.pie && (
          <div className="bg-white p-4 rounded-lg border border-neutral-200 lg:col-span-2">
            <ReactECharts 
              option={chartOptions.pie} 
              style={{ height: '300px' }}
              opts={{ renderer: 'canvas' }}
            />
          </div>
        )}
      </div>
    </div>
  )
}
