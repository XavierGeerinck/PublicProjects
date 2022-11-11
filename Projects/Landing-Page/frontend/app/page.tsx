export default function Home() {
  return (
    <div className="h-screen w-screen bg-primary flex flex-col items-center justify-center p-8 md:p-0">
      <h1 className="text-3xl font-extrabold text-accent">Coming soon!</h1>
      <h2 className="mt-2 text-lg text-white">Sign up to be notified</h2>

      <div className="mt-10 sm:mt-12">
        <form action="#" className="sm:mx-auto sm:max-w-xl lg:mx-0">
          <div className="sm:flex">
            <div className="min-w-0 flex-1">
              <label className="sr-only">Email address</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                className="block w-full rounded-md border-0 px-4 py-3 text-base text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-gray-900"
              />
            </div>
            <div className="mt-3 sm:mt-0 sm:ml-3">
              <button
                type="submit"
                className="block w-full rounded-md py-3 px-4 font-medium text-white shadow bg-accent focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-gray-900"
              >
                Sign Up
              </button>
            </div>
          </div>

          <p className="mt-3 text-sm text-gray-300 sm:mt-4">
            By providing your email and signing up, you agree to our{" "}
            <a href="#" className="font-medium text-white">
              terms of service
            </a>
            to be notified as soon as we launch.
          </p>
        </form>
      </div>
    </div>
  );
}
