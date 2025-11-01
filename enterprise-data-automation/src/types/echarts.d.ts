declare module 'echarts-for-react' {
  import * as React from 'react'
  
  interface EChartsReactProps {
    option: any
    style?: React.CSSProperties
    className?: string
    opts?: {
      renderer?: 'canvas' | 'svg'
      width?: number | string
      height?: number | string
    }
  }
  
  const EChartsReact: React.ComponentType<EChartsReactProps>
  export default EChartsReact
}