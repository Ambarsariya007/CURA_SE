import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import "./Signup.css"; // Assuming you have this CSS file for styling

const Signup = () => {
  // State to manage the selected role ('doctor' or 'patient')
  const [role, setRole] = useState(null);

  // State to manage form data, now including first_name and last_name
  const [formData, setFormData] = useState({
    first_name: "", // Added first_name
    last_name: "",  // Added last_name
    email: "",
    password: "",
    hospital: "", // Only for doctors
  });

  // State for displaying error messages
  const [error, setError] = useState(null);
  // State for managing loading status during API calls
  const [loading, setLoading] = useState(false);

  // Hook from react-router-dom for navigation
  const navigate = useNavigate();

  // Generic change handler for all input fields
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Handler for form submission
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default form submission behavior (page reload)
    setError(null);    // Clear any previous errors
    setLoading(true);  // Set loading to true

    // Backend registration endpoint
    const endpoint = "http://127.0.0.1:8000/register/";

    // Prepare data to send to the backend
    // Ensure that 'hospital' is only included for doctors, otherwise set to null
    const data = {
      first_name: formData.first_name,
      last_name: formData.last_name,
      email: formData.email,
      password: formData.password,
      role: role,
      hospital: role === "doctor" ? formData.hospital : null,
    };

    console.log("Sending data:", data); // Log the data being sent for debugging

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data), // Convert data object to JSON string
      });

      const result = await response.json(); // Parse the JSON response

      if (!response.ok) {
        // If response is not OK (e.g., 400 Bad Request), throw an error
        throw new Error(result.detail || result.email || "Registration failed"); // Improved error handling
      }

      // On successful registration
      console.log("Registration successful:", result);
      setFormData({ first_name: "", last_name: "", email: "", password: "", hospital: "" }); // Reset form
      setRole(null); // Reset role selection
      navigate("/"); // Redirect user to the home page or login page
    } catch (error) {
      console.error("Registration error:", error.message);
      setError(error.message); // Set the error state
    } finally {
      setLoading(false); // Always set loading to false after request completes
    }
  };

  return (
    <div className="register-container flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      {!role ? (
        // Role selection screen
        <div className="register-options bg-white p-8 rounded-lg shadow-lg flex flex-col gap-4 max-w-sm w-full">
          <motion.button
            className="btn-primary w-full py-3 px-6 rounded-md text-white font-semibold bg-blue-600 hover:bg-blue-700 transition-colors duration-300"
            whileHover={{ scale: 1.05 }}
            onClick={() => setRole("patient")}
          >
            Register as Patient
          </motion.button>
          <motion.button
            className="btn-outline w-full py-3 px-6 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition-colors duration-300"
            whileHover={{ scale: 1.05 }}
            onClick={() => setRole("doctor")}
          >
            Register as Doctor
          </motion.button>
        </div>
      ) : (
        // Registration form screen
        <motion.form
          className="register-form bg-white p-8 rounded-lg shadow-lg flex flex-col gap-4 max-w-md w-full"
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h2 className="text-2xl font-bold text-gray-800 mb-4 text-center">
            Register as {role === "doctor" ? "Doctor" : "Patient"}
          </h2>

          {error && <p className="error-message text-red-500 text-sm mb-4 text-center">{error}</p>}

          <input
            type="text"
            name="first_name"
            placeholder="First Name"
            value={formData.first_name}
            onChange={handleChange}
            className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <input
            type="text"
            name="last_name"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={handleChange}
            className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <input
            type="email"
            name="email"
            placeholder="Email Address"
            value={formData.email}
            onChange={handleChange}
            className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          {role === "doctor" && (
            <input
              type="text"
              name="hospital"
              placeholder="Currently working at (Hospital Name)"
              value={formData.hospital}
              onChange={handleChange}
              className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          )}
          <motion.button
            type="submit"
            className="btn-primary w-full py-3 px-6 rounded-md text-white font-semibold bg-green-600 hover:bg-green-700 transition-colors duration-300"
            whileHover={{ scale: 1.05 }}
            disabled={loading}
          >
            {loading ? "Registering..." : "Register"}
          </motion.button>
          <motion.button
            className="btn-outline w-full py-3 px-6 rounded-md text-gray-600 border border-gray-300 hover:bg-gray-50 transition-colors duration-300"
            whileHover={{ scale: 1.05 }}
            onClick={() => setRole(null)}
            type="button" // Important: set type="button" to prevent it from submitting the form
          >
            Back
          </motion.button>
        </motion.form>
      )}
    </div>
  );
};

export default Signup;
