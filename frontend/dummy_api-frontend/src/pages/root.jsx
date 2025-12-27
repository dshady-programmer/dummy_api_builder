import AppProvider from '../context.jsx';
import MyApi from './MyApi';
const Root = () => {
  return (
    <AppProvider>
        <MyApi />
    </AppProvider>
  )
}

export default Root
