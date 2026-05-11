export default function Loading() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] w-full">
            <div className="relative">
                <div className="w-14 h-14 rounded-full border-[3px] border-navy-700 border-t-teal-400 animate-spin" />
                <div className="absolute inset-0 w-14 h-14 rounded-full bg-teal-500/5 blur-xl" />
            </div>
            <p className="mt-6 text-sm text-gray-500 font-medium tracking-wide">Loading...</p>
        </div>
    )
}
