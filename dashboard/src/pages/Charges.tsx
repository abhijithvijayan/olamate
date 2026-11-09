import { api } from "../api/client";
import { usePolling } from "../api/hooks";
import { PageHeader } from "../components/Card";
import { SessionList } from "../components/SessionList";
import { EmptyState, ErrorState, LoadingState } from "../components/States";

export function Charges() {
  const charges = usePolling(() => api.sessions("charge", 50), 15000);

  return (
    <>
      <PageHeader title="Charges" subtitle="Charging sessions and how the pack filled up" />
      {charges.error && <ErrorState error={charges.error} onRetry={charges.refresh} />}
      {!charges.error && charges.loading && !charges.data && <LoadingState label="Loading charges" />}
      {!charges.error && charges.data && charges.data.length === 0 && (
        <EmptyState title="No charges yet">
          Charge sessions appear here once the collector records one. The collector detects charging when the charger is plugged in.
        </EmptyState>
      )}
      {charges.data && charges.data.length > 0 && <SessionList sessions={charges.data} basePath="/charges" />}
    </>
  );
}
