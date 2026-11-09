import { api } from "../api/client";
import { usePolling } from "../api/hooks";
import { PageHeader } from "../components/Card";
import { SessionList } from "../components/SessionList";
import { EmptyState, ErrorState, LoadingState } from "../components/States";

export function Rides() {
  const rides = usePolling(() => api.sessions("ride", 50), 15000);

  return (
    <>
      <PageHeader title="Rides" subtitle="Detected automatically whenever the scooter moves" />
      {rides.error && <ErrorState error={rides.error} onRetry={rides.refresh} />}
      {!rides.error && rides.loading && !rides.data && <LoadingState label="Loading rides" />}
      {!rides.error && rides.data && rides.data.length === 0 && (
        <EmptyState title="No rides yet">Take the scooter out with the collector running and the ride shows up here when you stop.</EmptyState>
      )}
      {rides.data && rides.data.length > 0 && <SessionList sessions={rides.data} basePath="/rides" />}
    </>
  );
}
