export default function Loading() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] w-full max-w-7xl mx-auto px-4">
            <div className="w-full max-w-3xl space-y-6">
                <div className="h-12 bg-navy-800 rounded-md animate-pulse w-3/4 mx-auto" />
                <div className="h-64 bg-navy-800 rounded-xl animate-pulse w-full" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="h-40 bg-navy-800 rounded-xl animate-pulse w-full" />
                    <div className="h-40 bg-navy-800 rounded-xl animate-pulse w-full" />
                </div>
            </div>
        </div>
    )
}
