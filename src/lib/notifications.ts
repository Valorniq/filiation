import { auth, db } from './firebase';
import { doc, updateDoc } from 'firebase/firestore';

export const NotificationService = {
  // Check if push notifications are supported
  isSupported: () => {
    return 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
  },

  // Request permission
  requestPermission: async () => {
    if (!NotificationService.isSupported()) {
      console.warn('Notifications not supported on this device/browser');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        console.log('Notification permission granted.');
        // In a real implementation with FCM, we would get the token here:
        // const token = await getToken(messaging, { vapidKey: '...' });
        // await NotificationService.saveTokenToUser(token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  },

  // Mock saving token
  saveTokenToUser: async (token: string) => {
    const user = auth.currentUser;
    if (user) {
      try {
        const userRef = doc(db, 'users', user.uid);
        await updateDoc(userRef, {
          fcmToken: token,
          notificationsEnabled: true,
          updatedAt: new Date().toISOString()
        });
      } catch (err) {
        console.error('Failed to save notification token:', err);
      }
    }
  },

  // Local notification fallback for demonstration
  showLocalNotification: (title: string, body: string) => {
    if (Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&q=80&w=192'
      });
    }
  }
};
